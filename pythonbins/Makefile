
all: help

help:
	@echo "This Makefile build checker binary from checker.py script."
	@echo "Requirements: Linux OS or Cygwin or Mingw-w64 with Python (>=3.7) of course."
	@echo "Export python3 to python or link it in windows, because python installer doesn't create a python3 command"
	@echo ""
	@echo "To build the binary use: make build"
	@echo ""

build: setup compile clean

setup:
	python3 -m venv venv; \
	. ./venv/bin/activate; \
	pip install -r ../python/requirements.txt; \
	pip install pyinstaller


compile:
	. ./venv/bin/activate; \
	pyinstaller -F ../python/checker.py; \
	mv dist/checker .


clean:
	rm -rf __pycache__ build dist venv *.spec
