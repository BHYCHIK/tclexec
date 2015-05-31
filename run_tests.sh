#!/bin/bash
for f in tests/*.tcl; do
    if [[ $f == tests/error_* ]]; then
        OUR_CMD="cat $f | ./tclexec.py 2>&1"
        TCLSH_CMD="cat $f.expected"
    else
        OUR_CMD="cat $f | ./tclexec.py"
        TCLSH_CMD="tclsh $f"
    fi
    DIFF_CMD="diff <($TCLSH_CMD) <($OUR_CMD)"
    eval $DIFF_CMD || { echo $TCLSH_CMD; echo $OUR_CMD; echo $DIFF_CMD; exit 1; }
    echo "$f ok"
done
