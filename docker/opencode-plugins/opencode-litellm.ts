// Loads the vendored fork of opencode-litellm (github.com/darwincr/opencode-litellm)
// mounted at ~/.config/opencode/opencode-litellm inside the container. Providers opt
// in via "litellm": true in their options; see modelFilter/modelDefaults there.
// Vendored from ~/.config/opencode/opencode-litellm on the workstation.
export { LiteLLMPlugin } from "../opencode-litellm/src/index.ts"
