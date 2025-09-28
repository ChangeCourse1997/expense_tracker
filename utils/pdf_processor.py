import pymupdf4llm
from datetime import datetime
import streamlit as st
import pandas as pd

class PDFProcessor:
    """Handles PDF processing and expense extraction."""
    
    def __init__(self):
        self.categories = {
            'Food & Dining': ['restaurant', 'food', 'coffee', 'lunch', 'dinner', 'cafe', 'pizza', 
                             'mcdonald', 'starbucks', 'subway', 'kfc', 'burger', 'taco', 'domino',
                             'curate kitchen', 'wokhey', 'koufu', 'tonkotsu', 'sukiya', 'jollibee',
                             'joe & dough', 'food panda', 'choco express', 'killineygo','twp - micron','wok hey','stuff\'d','tangled'],
            'Transportation': ['grab', 'lyft', 'taxi', 'gas', 'fuel', 'parking', 'metro', 'bus', 
                              'mrt', 'transit','tada','zig'],
            'Shopping': ['amazon', 'walmart', 'target', 'mall', 'store', 'purchase', 'ebay', 
                        'costco', 'bestbuy', 'home depot', 'lowes', 'shopee', 'uniqlo', 'zoff',
                         'popular book', 'taobao', 'bitp','andar'],
            'Utilities': ['electric', 'water', 'internet', 'phone', 'cable', 'utility', 'verizon', 
                         'att', 'comcast', 'spectrum', 'pge', 'gas company', 'gomo mobile'],
            'Healthcare': ['pharmacy', 'doctor', 'hospital', 'medical', 'health', 'cvs', 'walgreens', 
                          'clinic', 'dental', 'vision', 'accent dental'],
            'Entertainment': ['movie', 'netflix', 'spotify', 'game', 'entertainment', 'theater', 
                             'concert', 'hulu', 'disney', 'amazon prime', 'steam', 'steamgames'],
            'Groceries': ['grocery', 'supermarket', 'market', 'safeway', 'kroger', 'whole foods', 
                         'trader joe', 'publix', 'aldi', 'cold storage','don don donki'],
            'Banking': ['fee', 'charge', 'interest', 'transfer', 'atm', 'overdraft', 'conversion fee'],
            'Other': ['ccy conversion']
        }
        self.current_year = datetime.now().year  
    
    def categorize_expense(self, title):
        """
        Basic categorization logic based on title keywords.
        """
        title_lower = title.lower()
        
        for category, keywords in self.categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'Other'
        
    def extract_expenses_from_pdf(self, uploaded_file):
        """
        Extract expenses from uploaded PDF - wrapper for your original extract method.
        """
        try:
            print(f'EXTRACTING...')
            # Save uploaded file temporarily
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Call your original extract method
            df = self.extract(temp_path, uploaded_file.name)
            
            # Convert to list of dictionaries and add categories
            expenses = []
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    expense = {
                        'Date': row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                        'Title': row['title'],
                        'Amount': row['amount'],
                        'Category': self.categorize_expense(row['title'])
                    }
                    expenses.append(expense)
            
            return expenses
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return []
        finally:
            # Clean up temp file
            try:
                import os
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
    
    def extract(self, file_path, statement_file):
        """
        Your original extract method - keeping it exactly as you wrote it, with minor fixes.
        """
        markdown = pymupdf4llm.to_markdown(file_path)  # Use the file_path parameter
        start = False
        titles = []
        amounts = []
        date_raw = []
        
        for line in markdown.split('\n'):
            if 'KOK CHUN SHEN' in line:
                start = True
            if start:
                try:
                    dt = datetime.strptime(f"{line[:7]} {self.current_year}", "%d %b %Y")
                    expense = line.split()[-1]
                    title = ' '.join(line[7:].split()[:-1])
                    if '(' in expense:
                        expense = expense.replace('(','-').replace(')','')
                    titles.append(title)
                    amounts.append(float(expense))
                    date_raw.append(dt)      
                except:
                    pass
        
        # Move assertions outside the loop
        if titles and amounts and date_raw:
            assert len(titles) == len(amounts)
            assert len(amounts) == len(date_raw)
            
            df = pd.DataFrame({"date": date_raw, "title": titles, "amount": amounts})
            return df
        else:
            return pd.DataFrame(columns=["date", "title", "amount"])
        
        # Return empty dataframe for non-Citibank files
        return pd.DataFrame(columns=["date", "title", "amount"])