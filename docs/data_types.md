# Data types and structures

Details of certain data structures that appear in save data.

## String buffer
Holds pretty much any instance of user-inputted text, including the player 
character's name, multiplaye greetings, and skell names.

A string buffer consists of a variable length buffer containing the text, 
followed by a 4-byte integer holding the length of the string. Text is 
typically encoded in UTF-8, but some buffers in the original XCX hold text in 
UTF-16BE encoding.

In these documents, the size of the buffer is given including the string size, 
so a buffer that holds up to 60 characters would be described as a "sixty-four 
byte string buffer".