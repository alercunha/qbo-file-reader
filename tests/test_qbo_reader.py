import pytest
from qbo.reader import parse_date, parse_amount, QBOTransaction, QBOFile, QBOFileReader

def test_parse_date():
    date_str = '20220101123000[0:GMT]'
    expected_date = datetime(2022, 1, 1, 12, 30, 0)
    assert parse_date(date_str) == expected_date

def test_parse_amount():
    amount_str = '123.45'
    expected_amount = 123.45
    assert parse_amount(amount_str) == expected_amount

def test_qbo_transaction():
    data = {
        "TRNTYPE": "DEBIT",
        "DTPOSTED": "20220101123000[0:GMT]",
        "TRNAMT": "-123.45",
        "FITID": "123456",
        "NAME": "Test Transaction",
        "MEMO": "Test Memo"
    }
    transaction = QBOTransaction(data)
    assert transaction.type == "DEBIT"
    assert transaction.deposited == datetime(2022, 1, 1, 12, 30, 0)
    assert transaction.amount == -123.45
    assert transaction.id == "123456"
    assert transaction.name == "Test Transaction"
    assert transaction.memo == "Test Memo"

def test_qbo_file():
    headers = {"HEADER1": "VALUE1"}
    root = {
        "OFX": {
            "BANKMSGSRSV1": {
                "STMTTRNRS": {
                    "STMTRS": {
                        "BANKACCTFROM": {
                            "ACCTTYPE": "CHECKING",
                            "BANKID": "123456",
                            "ACCTID": "654321"
                        },
                        "BANKTRANLIST": {
                            "STMTTRN": {
                                "TRNTYPE": "DEBIT",
                                "DTPOSTED": "20220101123000[0:GMT]",
                                "TRNAMT": "-123.45",
                                "FITID": "123456",
                                "NAME": "Test Transaction",
                                "MEMO": "Test Memo"
                            }
                        }
                    }
                }
            }
        }
    }
    qbo_file = QBOFile(headers, root)
    assert qbo_file.headers == headers
    assert qbo_file.account_type == "CHECKING"
    assert qbo_file.bank_id == "123456"
    assert qbo_file.account_id == "654321"
    assert len(qbo_file.transactions) == 1
    transaction = qbo_file.transactions[0]
    assert transaction.type == "DEBIT"
    assert transaction.deposited == datetime(2022, 1, 1, 12, 30, 0)
    assert transaction.amount == -123.45
    assert transaction.id == "123456"
    assert transaction.name == "Test Transaction"
    assert transaction.memo == "Test Memo"

def test_qbo_file_reader():
    lines = [
        "HEADER1: VALUE1",
        "<OFX>",
        "<BANKMSGSRSV1>",
        "<STMTTRNRS>",
        "<STMTRS>",
        "<BANKACCTFROM>",
        "<ACCTTYPE>CHECKING</ACCTTYPE>",
        "<BANKID>123456</BANKID>",
        "<ACCTID>654321</ACCTID>",
        "</BANKACCTFROM>",
        "<BANKTRANLIST>",
        "<STMTTRN>",
        "<TRNTYPE>DEBIT</TRNTYPE>",
        "<DTPOSTED>20220101123000[0:GMT]</DTPOSTED>",
        "<TRNAMT>-123.45</TRNAMT>",
        "<FITID>123456</FITID>",
        "<NAME>Test Transaction</NAME>",
        "<MEMO>Test Memo</MEMO>",
        "</STMTTRN>",
        "</BANKTRANLIST>",
        "</STMTRS>",
        "</STMTTRNRS>",
        "</BANKMSGSRSV1>",
        "</OFX>"
    ]
    reader = QBOFileReader()
    for line in lines:
        reader.consume(line)
    qbo_file = QBOFile(reader.headers(), reader.root())
    assert qbo_file.headers == {"HEADER1": "VALUE1"}
    assert qbo_file.account_type == "CHECKING"
    assert qbo_file.bank_id == "123456"
    assert qbo_file.account_id == "654321"
    assert len(qbo_file.transactions) == 1
    transaction = qbo_file.transactions[0]
    assert transaction.type == "DEBIT"
    assert transaction.deposited == datetime(2022, 1, 1, 12, 30, 0)
    assert transaction.amount == -123.45
    assert transaction.id == "123456"
    assert transaction.name == "Test Transaction"
    assert transaction.memo == "Test Memo"
