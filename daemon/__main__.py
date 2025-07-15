"""
Main entry point for running the daemon as a module.
Allows running with: python -m daemon
"""
from daemon.processor import main

if __name__ == '__main__':
    main()
