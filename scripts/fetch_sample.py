from pathlib import Path

import yfinance as yf

start = '2023-01-01'
end = '2026-10-31'
freqncy = '1d'
tickers = ['0700.HK', '0005.HK', '0939.HK', '1299.HK', '0388.HK', '^HSI']
out_path = 'data/raw'


data = yf.download(tickers, start=start, end=end, interval=freqncy, auto_adjust=True, keepna=True, group_by='ticker')
print(f'Downloaded market data for {len(tickers)} tickers.')

output_dir = Path(out_path)
if not output_dir.exists():
    output_dir.mkdir(parents=True, exist_ok=True)

for ticker in tickers:
    ticker_data = data.xs(ticker, level='Ticker', axis=1).sort_values('Date')   
    parquet_file = output_dir / f'{ticker.replace(".", "_")}.parquet'
    ticker_data.to_parquet(parquet_file)
    print(f'Saved {ticker} data to {parquet_file}.')

print(f'Finished downloading and saving data to {output_dir}.')
