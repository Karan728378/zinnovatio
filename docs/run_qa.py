import sys, json, urllib.request
import pandas as pd

def check_seed():
    expected = {
        'data/seed/kilns.csv': ['kiln_id','name','lat','lon','village','monthly_fuel_tonnes'],
        'data/seed/suppliers.csv': ['supplier_id','name','kind','lat','lon','village','straw_form','price_per_tonne','available_tonnes'],
        'data/seed/deliveries.csv': ['delivery_id','kiln_id','supplier_id','date','tonnes','form','photo_ref']
    }
    for path, cols in expected.items():
        df = pd.read_csv(path)
        assert list(df.columns) == cols, f'Column mismatch in {path}'
        if 'name' in df.columns:
            assert df['name'].str.contains('Sample').all(), f'Missing Sample in {path}'
        print(f'[PASS] {path} ({len(df)} rows)')

def check_api(base):
    eps = ['/health','/config','/kilns','/kilns/K003/needs?month=2026-11','/kilns/K003/suppliers','/compliance/summary?month=2026-11']
    for ep in eps:
        try:
            with urllib.request.urlopen(base.rstrip('/') + ep, timeout=5) as r:
                print(f'[PASS] GET {ep} -> {r.status}')
        except Exception as e:
            print(f'[FAIL] GET {ep} -> {e}')

if __name__ == '__main__':
    check_seed()
    if '--api' in sys.argv:
        check_api(sys.argv[sys.argv.index('--api') + 1])
