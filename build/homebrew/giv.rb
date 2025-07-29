class Giv < Formula
  desc "{{DESCRIPTION}}"
  homepage "{{HOMEPAGE}}"
  version "{{VERSION}}"
  
  if Hardware::CPU.arm?
    url "{{MACOS_ARM64_URL}}"
    sha256 "{{MACOS_ARM64_SHA256}}"
  else
    url "{{MACOS_X86_64_URL}}"
    sha256 "{{MACOS_X86_64_SHA256}}"
  end

  def install
    bin.install Dir["*"].first => "giv"
  end

  test do
    system "#{bin}/giv", "--help"
  end
end
