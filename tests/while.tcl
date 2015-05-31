set a 1
set b 10
while "$a > $b" { puts "unreachable"}

while {$a < $b} {
    puts "while: a = $a"
    incr a
}
