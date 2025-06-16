#!/usr/bin/env python3
"""
Script to fix data inconsistency in journal entry lines.
This script identifies and fixes lines that have both payment_terms_id and due_date set,
which violates the business rule.
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.journal_entry import JournalEntryLine


async def find_inconsistent_lines():
    """Find journal entry lines with both payment_terms_id and due_date set."""
    async with AsyncSessionLocal() as db:
        # Query for lines that have both payment_terms_id and due_date
        query = select(JournalEntryLine).where(
            JournalEntryLine.payment_terms_id.isnot(None),
            JournalEntryLine.due_date.isnot(None)
        )
        
        result = await db.execute(query)
        inconsistent_lines = result.scalars().all()
        
        return inconsistent_lines


async def fix_inconsistent_lines(strategy: str = "keep_payment_terms"):
    """
    Fix inconsistent journal entry lines.
    
    Args:
        strategy: 
            - "keep_payment_terms": Remove due_date, keep payment_terms_id
            - "keep_due_date": Remove payment_terms_id, keep due_date
    """
    
    if strategy not in ["keep_payment_terms", "keep_due_date"]:
        raise ValueError("Strategy must be 'keep_payment_terms' or 'keep_due_date'")
    
    async with AsyncSessionLocal() as db:
        # Find inconsistent lines
        inconsistent_lines = await find_inconsistent_lines()
        
        if not inconsistent_lines:
            print("No inconsistent lines found.")
            return
        
        print(f"Found {len(inconsistent_lines)} inconsistent lines.")
        
        for line in inconsistent_lines:
            print(f"Line ID: {line.id}, Journal Entry ID: {line.journal_entry_id}")
            print(f"  Payment Terms ID: {line.payment_terms_id}")
            print(f"  Due Date: {line.due_date}")
            
        # Ask for confirmation
        response = input(f"\nDo you want to fix these lines using strategy '{strategy}'? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
        
        # Apply fixes
        fixed_count = 0
        for line in inconsistent_lines:
            try:
                if strategy == "keep_payment_terms":
                    # Remove due_date, keep payment_terms_id
                    line.due_date = None
                    print(f"Fixed line {line.id}: Removed due_date, kept payment_terms_id")
                else:  # keep_due_date
                    # Remove payment_terms_id, keep due_date
                    line.payment_terms_id = None
                    print(f"Fixed line {line.id}: Removed payment_terms_id, kept due_date")
                
                line.updated_at = datetime.utcnow()
                fixed_count += 1
                
            except Exception as e:
                print(f"Error fixing line {line.id}: {e}")
        
        # Commit changes
        try:
            await db.commit()
            print(f"\nSuccessfully fixed {fixed_count} lines.")
        except Exception as e:
            await db.rollback()
            print(f"Error committing changes: {e}")
            raise


async def report_inconsistent_lines():
    """Generate a report of inconsistent lines."""
    inconsistent_lines = await find_inconsistent_lines()
    
    if not inconsistent_lines:
        print("No inconsistent lines found.")
        return
    
    print(f"Data Inconsistency Report - {datetime.now()}")
    print("=" * 60)
    print(f"Found {len(inconsistent_lines)} journal entry lines with data inconsistency:")
    print("(Lines with both payment_terms_id and due_date set)")
    print()
    
    for line in inconsistent_lines:
        print(f"Line ID: {line.id}")
        print(f"  Journal Entry ID: {line.journal_entry_id}")
        print(f"  Line Number: {line.line_number}")
        print(f"  Account ID: {line.account_id}")
        print(f"  Payment Terms ID: {line.payment_terms_id}")
        print(f"  Due Date: {line.due_date}")
        print(f"  Debit Amount: {line.debit_amount}")
        print(f"  Credit Amount: {line.credit_amount}")
        print(f"  Created At: {line.created_at}")
        print(f"  Updated At: {line.updated_at}")
        print("-" * 40)


async def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_journal_entry_data_inconsistency.py report")
        print("  python fix_journal_entry_data_inconsistency.py fix [keep_payment_terms|keep_due_date]")
        print()
        print("Commands:")
        print("  report                   - Show inconsistent lines")
        print("  fix keep_payment_terms   - Fix by removing due_date, keeping payment_terms_id")
        print("  fix keep_due_date        - Fix by removing payment_terms_id, keeping due_date")
        return
    
    command = sys.argv[1].lower()
    
    if command == "report":
        await report_inconsistent_lines()
    elif command == "fix":
        if len(sys.argv) < 3:
            print("Error: fix command requires a strategy (keep_payment_terms or keep_due_date)")
            return
        
        strategy = sys.argv[2].lower()
        if strategy not in ["keep_payment_terms", "keep_due_date"]:
            print("Error: strategy must be 'keep_payment_terms' or 'keep_due_date'")
            return
        
        await fix_inconsistent_lines(strategy)
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
