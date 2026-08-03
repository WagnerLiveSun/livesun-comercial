"""
Simple OFX file parser for bank statement imports.
Supports basic OFX 1.x format extraction.
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional


class OFXTransaction:
    """Represents a single transaction from OFX file"""
    
    def __init__(self, trntype: str, dtposted: str, trnamt: str, fitid: str,
                 name: str = '', memo: str = '', reference: str = '', source_line: Optional[int] = None):
        self.trntype = trntype  # 'DEBIT', 'CREDIT', 'INT', 'DIV', 'XFER', 'CHECK'
        self.dtposted = dtposted  # YYYYMMDD
        self.trnamt = Decimal(trnamt)
        self.fitid = fitid  # Transaction ID for deduplication
        self.name = name  # Payee/Name
        self.memo = memo  # Description
        self.reference = reference  # Reference number
        self.source_line = source_line  # Approx line in OFX file where STMTTRN starts
    
    def to_dict(self) -> Dict:
        return {
            'tipo': self.trntype,
            'data': self._parse_date(self.dtposted),
            'valor': self.trnamt,
            'descricao': f"{self.name} - {self.memo}".strip(),
            'referencia': self.reference or self.fitid,
            'transaction_id': self.fitid,
            'tipo_movimento': 'entrada' if self.trnamt > 0 else 'saida',
            'source_line': self.source_line,
        }
    
    @staticmethod
    def _parse_date(ofx_date: str) -> Optional[datetime]:
        """Parse OFX date format YYYYMMDD or YYYYMMDDHHMM"""
        try:
            if len(ofx_date) >= 8:
                return datetime.strptime(ofx_date[:8], '%Y%m%d').date()
        except ValueError:
            pass
        return None


class OFXParser:
    """Simple OFX 1.x file parser"""
    
    def __init__(self, content: str):
        self.content = content
        self.transactions: List[OFXTransaction] = []
        self.account_id = None
        self.routing_number = None
        self.errors: List[str] = []
    
    def parse(self) -> bool:
        """Parse OFX content and extract transactions"""
        try:
            # Remove OFXHEADER and other control info if present
            lines = self.content.split('\n')
            ofx_content = '\n'.join(lines)
            
            # Extract account info
            self._extract_account_info(ofx_content)
            
            # Extract transactions
            self._extract_transactions(ofx_content)
            
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f'Erro ao processar arquivo OFX: {str(e)}')
            return False
    
    def _extract_account_info(self, content: str):
        """Extract bank account information"""
        # Look for BANKID
        bankid_match = re.search(r'<BANKID>(\d+)', content)
        if bankid_match:
            self.routing_number = bankid_match.group(1)
        
        # Look for ACCTID
        acctid_match = re.search(r'<ACCTID>(\d+)', content)
        if acctid_match:
            self.account_id = acctid_match.group(1)
    
    def _extract_transactions(self, content: str):
        """Extract individual transactions from OFX"""
        # Match transaction blocks: <STMTTRN>...</STMTTRN>
        transaction_pattern = r'<STMTTRN>.*?</STMTTRN>'

        for match in re.finditer(transaction_pattern, content, re.DOTALL):
            txn_block = match.group(0)
            try:
                source_line = content.count('\n', 0, match.start()) + 1
                txn = self._parse_transaction(txn_block, source_line)
                if txn:
                    self.transactions.append(txn)
            except Exception as e:
                self.errors.append(f'Erro ao processar transação: {str(e)}')
    
    def _parse_transaction(self, txn_block: str, source_line: Optional[int] = None) -> Optional[OFXTransaction]:
        """Parse single transaction block"""
        # Extract fields using regex
        trntype = self._extract_field(txn_block, 'TRNTYPE')
        dtposted = self._extract_field(txn_block, 'DTPOSTED')
        trnamt = self._extract_field(txn_block, 'TRNAMT')
        fitid = self._extract_field(txn_block, 'FITID')
        refnum = self._extract_field(txn_block, 'REFNUM')
        checknum = self._extract_field(txn_block, 'CHECKNUM')
        name = self._extract_field(txn_block, 'NAME')
        memo = self._extract_field(txn_block, 'MEMO')
        
        if not all([trntype, dtposted, trnamt, fitid]):
            return None
        
        return OFXTransaction(
            trntype=trntype,
            dtposted=dtposted,
            trnamt=trnamt,
            fitid=fitid,
            name=name,
            memo=memo,
            reference=refnum or checknum or fitid,
            source_line=source_line,
        )
    
    @staticmethod
    def _extract_field(block: str, field_name: str) -> str:
        """Extract OFX field value"""
        pattern = rf'<{field_name}>([^<]*)'
        match = re.search(pattern, block)
        return match.group(1).strip() if match else ''
    
    def get_transactions(self) -> List[Dict]:
        """Get parsed transactions as dictionaries"""
        return [txn.to_dict() for txn in self.transactions]
    
    def get_errors(self) -> List[str]:
        """Get parsing errors"""
        return self.errors
