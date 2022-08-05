from datetime import date, datetime
import statistics


class TestData:
    # Timestamps
    init_t = []
    final_t = []
    # Returned Data
    responses = []

    def getInitT(self):
        return self.init_t

    def addIniTimestamp(self, timestamp):
        self.init_t.append(timestamp)

    def addFinTimestamp(self, timestamp):
        self.final_t.append(timestamp)

    def getResponses(self):
        return self.responses

    def addResponse(self, response):
        self.responses.append(response)

    def clearData(self):
        self.final_t.clear()
        self.init_t.clear()
        self.responses.clear()

    # Obatin final output to return at the end of benchmark
    def computeRunTimes(self):
        if len(self.init_t) != len(self.final_t):
            return "Mismathing lenghts"
        else:
            deltas = []
            for i in range(0, len(self.init_t)):
                deltas.append((self.final_t[i] - self.init_t[i]).total_seconds())

            avg = statistics.mean(deltas)
            stddev = statistics.stdev(deltas)
            output = {"output": self.getResponses()}
            output["average"] = avg
            output["stddev"] = stddev

            return output
