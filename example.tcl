set greeting1 Sal 
set greeting2 ut
set greeting3 ations


#semicolon also delimits commands
set greeting1 Sal; set greeting2 ut; set greeting3 ations 


# Dollar sign introduces variable substitution
set greeting $greeting1$greeting2$greeting3
set {first bane} New
set greeting "Hello, ${first name}"
set greeting "Hello, [set {first name}]"
set {*}{name Neo}
set person(name) Neo
set greeting "Hello, $person(name)"
set c [expr {$a + $b}]

if {3 > 4} {
    puts {This will never happen}
} elseif {4 > 4} {
    puts {This will also never happen}
} else {
    puts {This will always happen}
}
set greeting "Hello, ${first name}"

puts " { a } "
set a   b
