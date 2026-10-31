from pathlib import Path

import yfinance as yf

start = '2023-01-01'
end = '2026-10-31'
freqncy = '1d'
stock_tickers = ['0700.HK', '0005.HK', '0939.HK', '1299.HK', '0388.HK', '^HSI']
crypto_ticker = ['BTC-USD', 'ETH-USD']
out_path = 'data/raw'



output_dir = Path(out_path)
if not output_dir.exists():
    output_dir.mkdir(parents=True, exist_ok=True)


def download_and_save_data(tickers, output_dir):
    data = yf.download(tickers, start=start, end=end, interval=freqncy, auto_adjust=True, keepna=True, group_by='ticker')
    print(f'Downloaded market data for {len(tickers)} tickers.')
    for ticker in tickers:
        ticker_data = data.xs(ticker, level='Ticker', axis=1).dropna(axis = 0, subset='Close').sort_values('Date')   
        parquet_file = output_dir / f'{ticker.replace(".", "_")}.parquet'
        ticker_data.to_parquet(parquet_file)
        print(f'Saved {ticker} data to {parquet_file}.')

download_and_save_data(stock_tickers, output_dir)
download_and_save_data(crypto_ticker, output_dir)

print(f'Finished downloading and saving data to {output_dir}.')
