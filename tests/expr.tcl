set b 10
set a [
  set b
  set b; set b
]
set c 2
set a [expr {$b / $c+2}]
puts [set a]
puts [expr $a / $c + 5]
puts [expr $a/$b+1]
