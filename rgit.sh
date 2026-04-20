#!/bin/bash

if [ ! -z "$VIRTUAL_ENV" ]
then
    VN=`basename $VIRTUAL_ENV`
else
    VN=""
fi

if [ -L $0 ]
then
    S=`readlink $0`
    P=`dirname $S`
else
    P=`dirname $0`
fi

if [ "$VN" != "rg" ]
then
    if [ ! -d "$P/rg" ]
    then
	echo "create venv"
	python3 -m venv "$P/rg"
	echo "activate"
	source $P/rg/bin/activate 
	echo "-> '$VIRTUAL_ENV'" 
	echo " pip install"
	python3 -m pip install -r $P/requirements.txt
	echo " pip done"
	python3 -m pip freeze
    else
    echo "activate"
	source $P/rg/bin/activate 
    fi
fi
"$P/rgit.py"
