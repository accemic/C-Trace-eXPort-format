FROM debian:bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    make \
    gcc-riscv64-unknown-elf \
    binutils-riscv64-unknown-elf \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /work
