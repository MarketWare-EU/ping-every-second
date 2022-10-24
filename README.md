
# Ping Every Second

With this Activegate extension, you can monitor the network latency and availability with a one-second resolution. The extension uses the standard ping command to continuously ping the target device. Each minute, the information is aggregated and inserted into several metrics, including *min*, *avg* and *max* values. Availability for each minute is also included. With this increased resolution, detailed information about performance can be gathered. Availability is measured up to "*five nines*", within a timeframe of up to one week.

---

Configuration begins by filling a set of requirements on the ActiveGate. At the moment, this extension is only available for Linux ActiveGates. Naturally, the ActiveGate will need to be able to communicate with the desired endpoints to be monitored with the system ping command.

On the ActiveGate machine, a ping command needs to be executed. This command needs to be executed for each and every one of the IPs to monitor. As can be seen below, besides specifying the destination for the ping command, you also have to exactly put the same IP in the name of the output file, in this case, the `/tmp/dyna_<ip>` file. An example for an hypothetical monitoring for IP `1.1.1.1`:

`nohup ping -D -O -s 16 1.1.1.1 >> /tmp/dyna_1.1.1.1 &`

The ActiveGate process needs read and write permission on files `/tmp/dyna_<ip>`.
Typically, the user is `dtuserag`, so the following example command should suffice (execute after the command above):

    chown dtuserag:dtuserag /tmp/dyna_<ip>

As can be observed, the first command (nohup ping) was executed with the options:
- `-D` : prints a timestamp in the output in the `/tmp` files. It is not used at the moment, but might be used in the near future.
- `-O` : essential for availability calculation. Given the one second frequency, typically one second will be the maximum latency value. Missed packets are identified by the string "no answer yet" in the ping output.
- `-s 16` : given so that ICMP packets are the smallest possible. Some systems might not support it, and others might even support a smaller value, so other values might be given. Please notice that this might induce a daily total of approximately 5MB of traffic in each direction:
-- Total packet size might be 58 bytes, with 16+8 bytes for ICMP, 20 bytes for IP, and 14 bytes for Ethernet. Values might be different at different network points/technologies.

The ActiveGate extension, each minute, copies the `/tmp/dyna_<ip>` file to a `/tmp/dyna1_<ip>` file, and truncates the original file. It then processes the copied file and sends data to Dynatrace. The file will exist for one minute, until the next processing is done. At the moment, you have to guarantee that if the ping process dies, or the system restarts, the ping command is run again. The ping command is used as it doesn't require special privileges to run.
 
After the ping is running, upload the .ZIP extension to the Dynatrace platform. Detailed instructions on this process can be found [here](https://www.dynatrace.com/support/help/extend-dynatrace/extensions/development/extension-how-tos/deploy-an-activegate-plugin/#deploy-via-dynatrace-web-ui).

 

After that, the extension's UI configurations are visible. The needed fields to fill are:

- `Endpoint name`: name to show on the Dynatrace UI
- `Ping Address`: IP address to monitor (should be precisely the same as on the ping command above, executed prior to this configuration)
- `Choose ActiveGate`: choose, from the dropdown, the ActiveGate where the extension was previously deployed

Data is available through the “Metrics”/"Data explorer" menu. The following metrics are available at the moment (all values are averaged when aggregated):

- `PingEverySecond.availability`: availability is calculated considering the total amount of "no answer yet" replies received. Note that availability values for a minute have a typical 1/60 resolution (~1.67%).
- `PingEverySecond.RTT`: the summarized metric for network round-trip time. The main value of the metric is the average value obtained for each 60 seconds. But you can also get the min/max value for that one minute.

There are some known caveats or missing functionality:

- The extension only works at the moment in Linux ActiveGates.
- Notice that if you start a ping command and it is not correctly configured (with the same IP as set in the Dynatrace platform), disk usage will grow at about 7MB per day.
- There is no alert functionality at the moment. This is going to be added in the future; in the meantime, [Custom Alerts](https://www.dynatrace.com/support/help/shortlink/metric-events-for-alerting#create-a-metric-event) might be used for that functionality.
- The extension creates 2 data points per minute for each measurement, which translates into (2 x 60 x 24 x 365 x 0.001) 1051.2 DDUs per year.
