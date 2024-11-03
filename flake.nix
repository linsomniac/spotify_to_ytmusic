{
  description = "Flake for spotify_to_ytmusic";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = import nixpkgs {
            inherit system;
          };

          spotify2ytmusic = with pkgs;
            python3Full.pkgs.buildPythonApplication
              {
                pname = "spotify2ytmusic ";
                version = "0.1.0";
                pyproject = true;

                src = ./.;

                build-system = with python3Packages; [
                  poetry-core
                ];

                dependencies = with python3Full.pkgs; [
                  ytmusicapi
                ];
              };


          inherit (pkgs) bashInteractive mkShell;
        in
        {
          devShells.default = mkShell {
            buildInputs = [
              bashInteractive
              spotify2ytmusic
            ];
          };

          packages.default = spotify2ytmusic;
        }
      );
}
