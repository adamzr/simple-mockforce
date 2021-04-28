import pytest

from simple_mockforce import mock_salesforce
from simple_salesforce import Salesforce

from simple_mockforce.virtual import virtual_salesforce
from tests.utils import MOCK_CREDS


@mock_salesforce
def test_basic_query():
    virtual_salesforce.create_new_virtual_instance()
    salesforce = Salesforce(**MOCK_CREDS)

    salesforce.Contact.create({"Name": "Ozzy Osbourne"})

    results = salesforce.query("SELECT Id, Name FROM Contact LIMIT 1")
    records = results["records"]

    assert len(records) == 1
    record = records[0]
    assert record["Id"]
    assert record["Name"] == "Ozzy Osbourne"


@mock_salesforce
def test_where_basic_query():
    virtual_salesforce.create_new_virtual_instance()
    salesforce = Salesforce(**MOCK_CREDS)

    response = salesforce.Lead.create({"Name": "Jim Bean", "Title": "CDO"})
    sfdc_id = response["id"]
    response = salesforce.Lead.create({"Name": "Corey Taylor", "Title": "Singer"})

    results = salesforce.query(f"SELECT Id, Name FROM Lead WHERE Id = 'nothing'")
    records = results["records"]
    assert len(records) == 0

    results = salesforce.query(f"SELECT Id, Name FROM Lead WHERE Name = null")
    records = results["records"]
    assert len(records) == 0

    results = salesforce.query(
        f"SELECT Id, Name, Title FROM Lead WHERE Id = '{sfdc_id}'"
    )
    records = results["records"]
    assert len(records) == 1
    record = records[0]
    assert record["Id"] == sfdc_id
    assert record["Name"] == "Jim Bean"
    assert record["Title"] == "CDO"


@pytest.mark.parametrize(
    "operator,number,expected",
    [
        # <
        ("<", 100, 0),
        ("<", 120, 1),
        # <=
        ("<=", 100, 1),
        ("<=", 5, 0),
        # >
        (">", 101, 0),
        (">", 4, 1),
        # >=
        (">=", 100, 1),
        (">=", 999, 0),
    ],
)
@mock_salesforce
def test_where_comparison_query(operator, number, expected):
    pass
    virtual_salesforce.create_new_virtual_instance()
    salesforce = Salesforce(**MOCK_CREDS)

    response = salesforce.bulk.Lead.insert(
        [
            {
                "Name": "Kurt Cobain",
                "Title": "Nirvana Guitarist",
                "Human_Score__c": 100,
            },
            {"Name": "Paris Hilton", "Title": "no one knows"},
        ]
    )
    sfdc_id = response[0]["id"]

    results = salesforce.query(
        f"SELECT Id, Name, Human_Score__c FROM Lead WHERE Human_Score__c {operator} {number}"
    )
    records = results["records"]
    assert len(records) == expected

    if expected > 0:
        record = records[0]
        assert record["Id"] == sfdc_id
        assert record["Name"] == "Kurt Cobain"
        assert record["Human_Score__c"] == 100


@mock_salesforce
def test_where_complex_query():
    virtual_salesforce.create_new_virtual_instance()
    salesforce = Salesforce(**MOCK_CREDS)

    response = salesforce.SomeFamousPerson__c.create(
        {"Name": "Quentin Tarantino", "Title": "Director"}
    )
    tarantino_id = response["id"]
    response = salesforce.SomeFamousPerson__c.create(
        {"Name": "Steven Spielberg", "Title": "Director"}
    )
    spielberg_id = response["id"]
    response = salesforce.SomeFamousPerson__c.create(
        {"Name": "Amy Adams", "Title": "Actor"}
    )
    adams_id = response["id"]

    results = salesforce.query(
        f"SELECT Id, Name FROM SomeFamousPerson__c WHERE Name = 'Quentin Tarantino' OR Name = 'Amy Adams'"
    )
    records = results["records"]
    assert len(records) == 2
    record = records[0]
    assert record["Id"] == tarantino_id
    record = records[1]
    assert record["Id"] == adams_id

    results = salesforce.query(
        f"SELECT Id, Name FROM SomeFamousPerson__c WHERE (Title = 'Director' OR Name = 'Amy Adams') AND Id != null"
    )
    records = results["records"]
    assert len(records) == 3
    record = records[0]
    assert record["Id"] == tarantino_id
    record = records[1]
    assert record["Id"] == spielberg_id
    record = records[2]
    assert record["Id"] == adams_id

    results = salesforce.query(
        f"SELECT Id, Name FROM SomeFamousPerson__c WHERE (Title = 'Actor' OR Title = 'Director') AND Name = null"
    )
    records = results["records"]
    assert len(records) == 0

    results = salesforce.query(
        f"SELECT Id, Name FROM SomeFamousPerson__c WHERE (Title = 'Actor' OR Title = 'Director') AND (Name != null AND Name = 'Quentin Tarantino')"
    )
    records = results["records"]
    assert len(records) == 1
    record = records[0]
    assert record["Id"] == tarantino_id


@mock_salesforce
def test_order_by_query():
    virtual_salesforce.create_new_virtual_instance()
    salesforce = Salesforce(**MOCK_CREDS)

    salesforce.bulk.Account.insert(
        [
            {"Name": "Google", "AlexaRanking__c": 1},
            {"Name": "YouTube", "AlexaRanking__c": 2},
            {"Name": "Facebook", "AlexaRanking__c": 7},
        ]
    )

    results = salesforce.query("SELECT Id, Name FROM Account ORDER BY Name ASC")
    records = results["records"]

    record1 = records[0]
    record2 = records[1]
    record3 = records[2]

    assert record1["Name"] == "Facebook"
    assert record2["Name"] == "Google"
    assert record3["Name"] == "YouTube"
