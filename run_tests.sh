#!/bin/bash
for f in tests/*.tcl; do
    TCLSH_CMD="tclsh $f"
    OUR_CMD="cat $f | python ./tclexec.py"
    DIFF_CMD="diff <($TCLSH_CMD) <($OUR_CMD)"
    eval $DIFF_CMD || { echo $TCLSH_CMD; echo $OUR_CMD; echo $DIFF_CMD; exit 1; }
    echo "$f ok"
done
