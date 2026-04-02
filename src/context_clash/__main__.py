import os
import sys
from streamlit.web import cli as stcli

def main():
    # This points to the app.py in the same folder
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "app.py")
    sys.argv = ["streamlit", "run", filename]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
