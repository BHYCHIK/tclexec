set i 0
while {$i < 10} {
    incr i 2
}

puts "after while 1"
set i 0
while "$i < 10" {
    incr i 2
}
puts "after while 2"
