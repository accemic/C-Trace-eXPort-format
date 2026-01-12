RISCV_GCC ?= riscv64-unknown-elf-gcc
RISCV_OBJDUMP ?= riscv64-unknown-elf-objdump

# Keep this consistent with the existing examples in the repo.
# CSR instructions are used (csrw/csrr), so include zicsr.
ARCH ?= rv32imac_zicsr
ABI  ?= ilp32
TEXT ?= 0x80000000

SOURCES := $(wildcard *.S)
ELFS    := $(SOURCES:.S=.elf)

.PHONY: all clean

all: $(ELFS) dis

%.elf: %.S
	$(RISCV_GCC) -march=$(ARCH) -mabi=$(ABI) -nostdlib -Wl,-Ttext=$(TEXT) -o $@ $<

.PHONY: dis
dis: $(ELFS)
	@for f in $(ELFS); do \
	  base=$${f%.elf}; \
	  $(RISCV_OBJDUMP) -d $$f > ../$$base.dis; \
	done

clean:
	rm -f $(ELFS)
	rm -f ../*.dis
