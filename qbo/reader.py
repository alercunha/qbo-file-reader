import json
import sys
from datetime import datetime
from os import path


def parse_date(date_str):
    return datetime.strptime(date_str, '%Y%m%d%H%M%S[0:GMT]')


def parse_amount(amount_str):
    return float(amount_str)


class QBOTransaction:
    def __init__(self, data):
        self.type = data["TRNTYPE"]
        self.deposited = parse_date(data["DTPOSTED"])
        self.amount = parse_amount(data["TRNAMT"])
        self.id = data["FITID"]
        self.name = data["NAME"]
        self.memo = data.get("MEMO", None)


class QBOFile:
    headers = None
    root = None

    def __init__(self, headers, root):
        self.headers = headers
        self.root = root
        if root['OFX'].get('BANKMSGSRSV1', None):
            stmtrs = root['OFX']['BANKMSGSRSV1']['STMTTRNRS']['STMTRS']
            self.account_type = stmtrs['BANKACCTFROM']['ACCTTYPE']
            self.bank_id = stmtrs['BANKACCTFROM']['BANKID']
            self.account_id = stmtrs['BANKACCTFROM']['ACCTID']
        elif root['OFX'].get('CREDITCARDMSGSRSV1', None):
            stmtrs = root['OFX']['CREDITCARDMSGSRSV1']['CCSTMTTRNRS']['CCSTMTRS']
            self.account_type = 'CREDITCARD'
            self.bank_id = 'CREDITCARD'
            self.account_id = stmtrs['CCACCTFROM']['ACCTID']
        else:
            raise Exception('Unknown QBO account type')

        stmttrn = stmtrs['BANKTRANLIST']['STMTTRN']
        if isinstance(stmttrn, dict):
            stmttrn = [stmttrn]
        self.transactions = [QBOTransaction(t) for t in stmttrn]

    def print(self):
        for k, v in self.headers.items():
            print('{0}: {1}'.format(k, v))
        print(json.dumps(self.root, indent=4))


class QBOFileReader:
    _headers = dict()
    _queue = [dict()]
    _consume_func = None

    def __init__(self):
        self._consume_func = self.read_header

    def consume(self, line: str):
        line = line.strip()
        if line:
            self._consume_func(line)

    def read_header(self, line: str):
        if line.upper() == "<OFX>":
            self._consume_func = self.read_node
            self._consume_func(line)
        else:
            split = line.split(':')
            self._headers[split[0].strip()] = split[1].strip()

    def read_node(self, line: str):
        if line.startswith('</'):
            name = line[2:-1]
            data = self._queue.pop()
            if data['_name'] != name:
                raise Exception('Invalid closing: {0} - expected </{1}>'.format(line, data['_name']))
            data.pop('_name')
        elif line.startswith('<'):
            pos = line.find('>')
            if pos == -1:
                raise Exception('Invalid line: {0}'.format(line))
            name = line[1:pos]
            value = line[pos+1:]
            if value:
                self._queue[-1][name] = value
            else:
                data = {'_name': name}
                if name in self._queue[-1]:
                    other = self._queue[-1][name]
                    if not isinstance(other, list):
                        other = [other]
                        self._queue[-1][name] = other
                    other.append(data)
                else:
                    self._queue[-1][name] = data
                self._queue.append(data)

    def headers(self):
        return self._headers

    def root(self):
        return self._queue[0]


def read_file(filepath: str):
    with open(filepath, 'r') as file:
        lines = file.readlines()
    reader = QBOFileReader()
    for line in lines:
        reader.consume(line)
    return QBOFile(reader.headers(), reader.root())


if __name__ == '__main__':
    qbo_file = read_file(path.expanduser(sys.argv[1]))
    qbo_file.print()
