
from app.defense.threat_classification import ThreatClassification


def test_threat_classification_values():
    assert ThreatClassification.BENIGN.value == "benign"
    assert ThreatClassification.SUSPICIOUS.value == "suspicious"
    assert ThreatClassification.MALICIOUS.value == "malicious"
    assert ThreatClassification.UNKNOWN.value == "unknown"


def test_threat_classification_from_string():
    assert ThreatClassification("benign") == ThreatClassification.BENIGN
    assert ThreatClassification("suspicious") == ThreatClassification.SUSPICIOUS
    assert ThreatClassification("malicious") == ThreatClassification.MALICIOUS
    assert ThreatClassification("unknown") == ThreatClassification.UNKNOWN
