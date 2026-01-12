.PHONY: lint
.PHONY: examples-build examples-build-docker examples-clean
.PHONY: examples-verify

lint:
	python3 tools/ctxp_lint.py examples

# Build example ELF and disassembly artifacts.
#
# If you have a host toolchain installed (riscv64-unknown-elf-*), you can run:
#   make examples-build
# Otherwise use Docker:
#   make examples-build-docker
examples-build:
	$(MAKE) -C examples/_sources all

examples-clean:
	$(MAKE) -C examples/_sources clean

examples-build-docker:
	docker build -t ctxp-riscv-toolchain examples/_sources
	docker run --rm -u $$(id -u):$$(id -g) -v "$$(pwd)":/work -w /work/examples/_sources \
		ctxp-riscv-toolchain make all

# Sanity check: ensure trace-referenced code addresses appear in the corresponding .dis.
examples-verify:
	python3 tools/verify_examples.py
