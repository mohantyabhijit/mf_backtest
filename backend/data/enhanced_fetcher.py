"""
Enhanced data fetcher supporting multiple sources:
- Jugaad Data (NSE stocks, indices, derivatives)
- BSEData (BSE stocks and indices) 
- NSETools (live market data)
- NSEpy (historical data backup)
- Economic indicators
"""
import time
import requests
from datetime import datetime, date, timedelta
from backend.data.store import (
    upsert_bse_stock_batch, upsert_derivatives_batch, 
    upsert_economic_data_batch, upsert_volatility_batch,
    upsert_index_batch
)

# Import data source libraries
try:
    from jugaad_data.nse import stock_df, index_df
    from jugaad_data.nse import NSELive
    JUGAAD_AVAILABLE = True
except ImportError:
    print("jugaad-data not available")
    JUGAAD_AVAILABLE = False

try:
    from bsedata.bse import BSE
    BSE_AVAILABLE = True
except ImportError:
    print("bsedata not available")
    BSE_AVAILABLE = False

try:
    from nsetools import Nse
    NSETOOLS_AVAILABLE = True
except ImportError:
    print("nsetools not available") 
    NSETOOLS_AVAILABLE = False

try:
    from nsepy import get_history
    from nsepy.derivatives import get_expiry_date
    NSEPY_AVAILABLE = True
except ImportError:
    print("nsepy not available")
    NSEPY_AVAILABLE = False


class EnhancedDataFetcher:
    """Unified data fetcher supporting multiple Indian market data sources"""
    
    def __init__(self):
        self.jugaad_client = NSELive() if JUGAAD_AVAILABLE else None
        self.bse_client = BSE() if BSE_AVAILABLE else None  
        self.nse_client = Nse() if NSETOOLS_AVAILABLE else None
        
    def fetch_stock_history_jugaad(self, symbol: str, start_date: date, end_date: date) -> int:
        """Fetch stock history using jugaad-data"""
        if not JUGAAD_AVAILABLE:
            return 0
            
        try:
            df = stock_df(symbol=symbol, from_date=start_date, to_date=end_date, series="EQ")
            if df.empty:
                print(f"  [{symbol}] No data from jugaad-data")
                return 0
                
            rows = []
            for idx, row in df.iterrows():
                date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)[:10]
                rows.append((
                    symbol, date_str, 
                    float(row.get('OPEN', 0)), float(row.get('HIGH', 0)),
                    float(row.get('LOW', 0)), float(row.get('CLOSE', 0)),
                    int(row.get('VOLUME', 0)), float(row.get('VALUE', 0))
                ))
            
            if rows:
                upsert_bse_stock_batch(rows)  # Reusing BSE table for stock data
                print(f"  [{symbol}] Stored {len(rows)} records via jugaad-data")
            
            time.sleep(0.2)  # Be respectful to APIs
            return len(rows)
            
        except Exception as e:
            print(f"  [{symbol}] ERROR via jugaad-data: {e}")
            return 0
    
    def fetch_index_history_jugaad(self, index_name: str, start_date: date, end_date: date) -> int:
        """Fetch index history using jugaad-data"""
        if not JUGAAD_AVAILABLE:
            return 0
            
        try:
            # Map our internal index names to jugaad symbols
            jugaad_map = {
                'nifty_50_tri': 'NIFTY 50',
                'nifty_midcap_150_tri': 'NIFTY MIDCAP 150', 
                'nifty_smallcap_250_tri': 'NIFTY SMALLCAP 250',
                'nifty_500_tri': 'NIFTY 500'
            }
            
            jugaad_symbol = jugaad_map.get(index_name, index_name)
            df = index_df(symbol=jugaad_symbol, from_date=start_date, to_date=end_date)
            
            if df.empty:
                print(f"  [{index_name}] No data from jugaad-data")
                return 0
                
            rows = []
            for idx, row in df.iterrows():
                date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)[:10]
                close_value = row.get('CLOSE', row.get('Close', 0))
                rows.append((index_name, date_str, float(close_value)))
            
            if rows:
                upsert_index_batch(rows)
                print(f"  [{index_name}] Stored {len(rows)} records via jugaad-data")
            
            time.sleep(0.2)
            return len(rows)
            
        except Exception as e:
            print(f"  [{index_name}] ERROR via jugaad-data: {e}")
            return 0
    
    def fetch_bse_live_data(self, symbols: list) -> int:
        """Fetch live BSE data for given symbols"""
        if not BSE_AVAILABLE:
            return 0
            
        total_fetched = 0
        for symbol in symbols:
            try:
                quote = self.bse_client.getQuote(symbol)
                if quote and 'currentValue' in quote:
                    today = datetime.now().strftime('%Y-%m-%d')
                    # Store as single-day OHLC data
                    rows = [(
                        symbol, today,
                        float(quote.get('dayHigh', quote['currentValue'])),
                        float(quote.get('dayHigh', quote['currentValue'])),
                        float(quote.get('dayLow', quote['currentValue'])),
                        float(quote['currentValue']),
                        0, 0  # volume, value - not available in live quotes
                    )]
                    upsert_bse_stock_batch(rows)
                    total_fetched += 1
                    print(f"  [{symbol}] Live BSE quote: {quote['currentValue']}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"  [{symbol}] ERROR fetching BSE quote: {e}")
        
        return total_fetched
    
    def fetch_volatility_data(self, start_date: date, end_date: date) -> int:
        """Fetch India VIX and other volatility indices"""
        if not JUGAAD_AVAILABLE:
            return 0
            
        try:
            # Fetch India VIX data
            df = index_df(symbol='INDIA VIX', from_date=start_date, to_date=end_date)
            
            if df.empty:
                print("No India VIX data available")
                return 0
                
            rows = []
            for idx, row in df.iterrows():
                date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)[:10]
                vix_value = row.get('CLOSE', row.get('Close', 0))
                rows.append(('india_vix', date_str, float(vix_value)))
            
            if rows:
                upsert_volatility_batch(rows)
                print(f"Stored {len(rows)} India VIX records")
            
            return len(rows)
            
        except Exception as e:
            print(f"ERROR fetching volatility data: {e}")
            return 0
    
    def fetch_economic_indicators(self) -> int:
        """Fetch basic economic indicators from public APIs"""
        total_fetched = 0
        
        # Example: USD-INR exchange rate from a free API
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and 'INR' in data['rates']:
                    today = datetime.now().strftime('%Y-%m-%d')
                    usd_inr_rate = data['rates']['INR']
                    
                    rows = [('usd_inr_rate', today, float(usd_inr_rate), 'currency', 'exchangerate-api')]
                    upsert_economic_data_batch(rows)
                    print(f"Updated USD-INR rate: {usd_inr_rate}")
                    total_fetched += 1
                    
        except Exception as e:
            print(f"ERROR fetching USD-INR rate: {e}")
        
        return total_fetched


def fetch_enhanced_data(force: bool = False):
    """Main function to fetch data from all enhanced sources"""
    fetcher = EnhancedDataFetcher()
    
    print("=" * 60)
    print("Enhanced Data Fetcher - Multi-Source Update")
    print("=" * 60)
    
    # Fetch volatility data for last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n[1/4] Fetching volatility data ({start_date} to {end_date})...")
    vix_count = fetcher.fetch_volatility_data(start_date, end_date)
    
    print(f"\n[2/4] Fetching economic indicators...")
    econ_count = fetcher.fetch_economic_indicators()
    
    # Fetch some sample stock data
    print(f"\n[3/4] Fetching sample stock data...")
    sample_stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK']
    stock_count = 0
    for stock in sample_stocks:
        count = fetcher.fetch_stock_history_jugaad(stock, start_date, end_date)
        stock_count += count
    
    # Fetch enhanced index data
    print(f"\n[4/4] Fetching enhanced index data...")
    indices = ['nifty_50_tri', 'nifty_midcap_150_tri']
    index_count = 0
    for index in indices:
        count = fetcher.fetch_index_history_jugaad(index, start_date, end_date)
        index_count += count
    
    print("\n" + "=" * 60)
    print(f"Enhanced data fetch complete!")
    print(f"Volatility records: {vix_count}")
    print(f"Economic indicators: {econ_count}")  
    print(f"Stock records: {stock_count}")
    print(f"Index records: {index_count}")
    print("=" * 60)


if __name__ == "__main__":
    fetch_enhanced_data(force=True)