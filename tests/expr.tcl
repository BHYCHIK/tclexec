set b 10
set a [
  set b
  set b; set b
]
set c 2
set a [expr {$b / $c}]
puts [set a]
