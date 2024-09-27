import streamlit.web.cli as stcli
import sys
import os

if __name__ == '__main__':
    src = os.path.join(os.path.dirname(__file__), 'main.py')
    sys.argv = ['streamlit', 'run', src, '--server.port=9009', '--global.developmentMode=false']
    sys.exit(stcli.main())