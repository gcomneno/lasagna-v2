"""
Compat wrapper per la CLI Lasagna v2 (univariate MVP).

Permette ancora di usare:
    python lasagna_mvp.py encode ...
    python lasagna_mvp.py info ...
"""

from lasagna2.cli import main

if __name__ == "__main__":
    main()
