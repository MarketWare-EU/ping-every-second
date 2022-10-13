import requests
from ruxit.api.base_plugin import RemoteBasePlugin
import logging
import os
import re
from datetime import datetime,timezone

logger = logging.getLogger(__name__)

class PingEverySecond(RemoteBasePlugin):
	def initialize(self, **kwargs):
		self.pingAddress = self.config["pingAddress"]
		self.tenant = self.config["tenant"]
		self.api_token = self.config["api_token"]
		self.debugLevel = self.config["debugLevel"]
		if self.debugLevel > 1:
			logger.info("Config: %s", self.config)

	def query(self, **kwargs):
		try:
			os.system("cp /tmp/dyna_" + self.pingAddress + " /tmp/dyna1_" + self.pingAddress)
			os.system("truncate --size=0 /tmp/dyna_" + self.pingAddress)
			maxRtt=0
			minRtt=10000
			totalPings=0
			totalErrors=0
			sumRtt=0
			firstLine=1
			firstTime=""
			lastTime=""
			with open('/tmp/dyna1_' + self.pingAddress) as inf:
				for line in inf:
					#Expecting a line like: [1664733901.759534] 24 bytes from 1.1.1.1: icmp_seq=51694 ttl=58 time=9.13 ms
					if firstLine==1:
						firstTime=re.findall("^\[([0-9\.]+)\]", line)
						firstLine=0
					lastTime=re.findall("^\[([0-9\.]+)\]", line)
					valorLinha=re.findall("time=([0-9\.]+) ms", line)
					if len(valorLinha)==1:
						rtt=float(valorLinha[0])
						if rtt>maxRtt:
							maxRtt=rtt
						if rtt<minRtt:
							minRtt=rtt
						sumRtt+=rtt
						totalPings+=1
					elif re.search("no answer yet", line):
						totalErrors+=1
			str_minRtt = str(round(minRtt,2))
			str_maxRtt = str(round(maxRtt,2))
			str_sumRtt = str(round(sumRtt,2))
			str_dataTime=""
			if len(firstTime)==1 and len(lastTime)==1:
				UTCtime = float(datetime.now(timezone.utc).timestamp())
				periodTime = float( float(lastTime[0]) - float(firstTime[0]) )
				print("#######periodTime=" + str(periodTime/2))
				str_dataTime = str( int(1000 * (UTCtime - (periodTime/2))) )
				if self.debugLevel > 2:
					logger.info("UTCtime=" + str(UTCtime) + " firstTime="+str(firstTime[0]) + " lastTime=" + str(lastTime[0]) + " dataTime=" + str_dataTime )



			if self.debugLevel > 0:
				logger.info("Min: %.2f Avg: %.2f Max: %.2f Avail: %.2f Ping RTT: #Success: %.0f #Errors: %.0f" % (minRtt,float(sumRtt/totalPings),maxRtt,100*totalPings/(totalPings+totalErrors),totalPings,totalErrors))

			lineProtocol = "#PingEverySecond.RTT gauge dt.meta.unit=MilliSecond,dt.meta.description=\"Ping Every Second RTT\",dt.meta.displayname=\"Ping Every Second RTT\"\n"
			lineProtocol += "PingEverySecond.RTT,endpoint=" + self.pingAddress + " gauge,min=" + str_minRtt + ",max=" + str_maxRtt + ",sum=" + str_sumRtt + ",count=" + str(totalPings) + " " + str_dataTime + "\n"
			lineProtocol += "PingEverySecond.availability,endpoint=" + self.pingAddress + " " + str(float(100*totalPings/(totalPings+totalErrors))) + " " + str_dataTime
			if self.debugLevel > 2:
				logger.info("lineProtocol=" + lineProtocol)
			ingestURL = "https://localhost:9999/e/" + self.tenant + "/api/v2/metrics/ingest"

			headers = {'Authorization': 'Api-Token ' + self.api_token, 'Content-Type': 'text/plain; charset=utf-8', 'accept': 'application/json; charset=utf-8' }
			response = requests.post(ingestURL, data=lineProtocol, headers=headers, timeout=5, verify=False)
			if self.debugLevel > 2:
				logger.info("API HTTP response=" + str(response.status_code) + " Body Response=" + str(response.text) ) 

		except Exception as e:
			device.state_metric(key='avgPingRTT', value='ERROR')
			logger.error("pingEverySecond Problem %s: %s." % (self.pingAddress, e))

