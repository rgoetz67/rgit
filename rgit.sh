#!/bin/bash

if [ ! -z "$VIRTUAL_ENV" ]
then
    VN=`basename $VIRTUAL_ENV`
else
    VN=""
fi

P=`dirname $0`

if [ "$VN" != "rg" ]
then
    echo "activate"
    source $P/rg/bin/activate 
    echo $VIRTUAL_ENV
fi
"$P/rgit.py"
