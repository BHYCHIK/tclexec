set x 999
puts $x
proc my_proc {a b} {
    set x 123
    set c [expr $a + $b]
}
set g [my_proc 3 8]
puts $g
puts $x
