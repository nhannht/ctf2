CXX      ?= g++

# Default: minimal protections (for original challenge feel)
CXXFLAGS ?= -std=c++17 -O0 -fno-stack-protector -no-pie -w

# Standard pwn-challenge protections, symbols kept (no DWARF locals).
#   - Stack canary:   -fstack-protector-strong
#   - PIE:            -fPIE -pie
#   - RELRO+BIND_NOW: -Wl,-z,relro,-z,now
#   - NX:             -Wl,-z,noexecstack
#   - No -g           (so locals/types are not exposed)
#   - No strip        (function/global names stay in symbol table)
HARDFLAGS = -std=c++17 -O0 \
            -fstack-protector-strong \
            -fPIE -pie \
            -Wl,-z,relro,-z,now \
            -Wl,-z,noexecstack \
            -w

prob: prob.cc
	$(CXX) $(CXXFLAGS) -o $@ $<

# Build the hardened version (keeps symbols).
hard: prob.cc
	$(CXX) $(HARDFLAGS) -o prob $<
	@echo
	@echo "=== protections ==="
	@which checksec >/dev/null 2>&1 && checksec --file=prob || \
	    (echo 'install pwntools/checksec for the report'; \
	     readelf -d prob | grep -E 'BIND_NOW|NX|RELRO' || true)
	@echo
	@echo "=== symbol kept (sample) ==="
	@nm prob 2>/dev/null | grep -E ' (T|t|B|b|D|d) ' | grep -E 'cage|books|cmd_|main' | head -20

clean:
	rm -f prob prob_hard

.PHONY: clean hard
