# sip tutorial notes

## introduxion

* sip server needed to handle incoming calls from trunk
* sip takes care of signaling, rtp of media content
* UAC is the one who makes call, UAS is the receiver

# SIP methods

1. INVITE: initiate the call
2. BYE: terminate 
3. CANCEL: terminate before 200 OK
4. INFO: mid call info, such as DTMF
5. MESSAGE: instant messanges (?)
6. NOTIFY: ?o


# AUTHENTICATION

In our case, we might need digest authentication (hashed user-pass)

