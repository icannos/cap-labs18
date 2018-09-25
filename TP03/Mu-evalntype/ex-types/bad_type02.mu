if (1 == "foo")
    log 42;
else
    log "the answer";

# EXITCODE 1
# EXPECTED
# Line 1 col 4: invalid type for relational operands: integer and string
# EXITCODE 1
