{
  description = "studiwize landing page — static HTML/CSS/JS dev environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system}; in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs_22   # tooling (lint, format, puppeteer for OG image if needed)
            python3     # python -m http.server 8000 for local preview
          ];
          shellHook = ''
            echo "studiwize dev shell"
            echo "  node    $(node --version)"
            echo "  python  $(python3 --version)"
            echo ""
            echo "  preview → python3 -m http.server 8000"
          '';
        };
      });
}
