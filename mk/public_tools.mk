PROVIDER_PRESET ?= light
PROVIDER_WAV ?= data/sample/vosk_test.wav
PROVIDER_LANGUAGE ?= en-US
PROVIDER_SETTINGS_JSON ?= {}
PROVIDER_CHECK_ARGS ?=

.PHONY: public-help init-provider-env configure-providers configure-provider preflight-provider provider-validate provider-test public-release-check prepare-ui-assets prepare-runtime-assets prepare-benchmark-assets prepare-hf-benchmark-assets prepare-hf-local-assets prepare-hf-api-assets

configure-providers:
	bash scripts/init_provider_env.sh --prompt-all

configure-provider:
	bash scripts/init_provider_env.sh --prompt-provider "$(PROVIDER_PROFILE)"

preflight-provider:
	bash scripts/run_provider_preflight.sh "$(PROVIDER_PROFILE)"

prepare-ui-assets:
	bash scripts/prepare_provider_startup.sh ui "$(PROVIDER_PROFILE)"

prepare-runtime-assets:
	bash scripts/prepare_provider_startup.sh runtime "$(PROVIDER_PROFILE)"

prepare-benchmark-assets:
	bash scripts/prepare_benchmark_startup.sh "$(BENCHMARK_PROFILE)"

prepare-hf-benchmark-assets:
	bash scripts/prepare_benchmark_startup.sh huggingface_provider_matrix

prepare-hf-local-assets:
	bash scripts/prepare_provider_startup.sh runtime providers/huggingface_local

prepare-hf-api-assets:
	bash scripts/prepare_provider_startup.sh runtime providers/huggingface_api

up web-gui web-gui-lan: prepare-ui-assets
web-gui web-gui-lan: build
up-runtime run: prepare-runtime-assets
bench bench-suite: prepare-benchmark-assets
bench-hf: prepare-hf-benchmark-assets
hf-smoke-local: prepare-hf-local-assets
hf-smoke-api: prepare-hf-api-assets

public-help:
	@printf '%s\n' \
		'Public setup and provider commands:' \
		'  make up                                        Prepare local assets, guide optional setup, preflight, then start UI' \
		'  make up-runtime PROVIDER_PROFILE=...            Prepare and preflight the selected provider before runtime start' \
		'  make bench-suite                               Prepare every configured benchmark provider before execution' \
		'  make configure-providers                       Reopen optional provider setup' \
		'  make configure-provider PROVIDER_PROFILE=...    Configure one provider interactively' \
		'  make preflight-provider PROVIDER_PROFILE=...    Check whether one provider is launch-ready' \
		'  make init-provider-env                         Create secrets/local/runtime.env safely' \
		'  make provider-validate PROVIDER_PROFILE=...    Validate the selected backend through the gateway' \
		'  make provider-test PROVIDER_PROFILE=...        Run a real WAV transcription with the selected backend' \
		'  make public-release-check                      Run static checks before sharing the repository' \
		'' \
		'Provider-check variables:' \
		'  PROVIDER_PRESET=light' \
		'  PROVIDER_WAV=data/sample/vosk_test.wav' \
		'  PROVIDER_LANGUAGE=en-US' \
		'  PROVIDER_SETTINGS_JSON={}' \
		'  PROVIDER_CHECK_ARGS="--timeout-sec 120"'

init-provider-env:
	bash scripts/init_provider_env.sh

provider-validate:
	python3 scripts/provider_gateway_check.py validate \
		--base-url "$(GATEWAY_URL)" \
		--profile "$(PROVIDER_PROFILE)" \
		--preset "$(PROVIDER_PRESET)" \
		--settings-json '$(PROVIDER_SETTINGS_JSON)' \
		$(PROVIDER_CHECK_ARGS)

provider-test:
	python3 scripts/provider_gateway_check.py test \
		--base-url "$(GATEWAY_URL)" \
		--profile "$(PROVIDER_PROFILE)" \
		--preset "$(PROVIDER_PRESET)" \
		--settings-json '$(PROVIDER_SETTINGS_JSON)' \
		--wav-path "$(PROVIDER_WAV)" \
		--language "$(PROVIDER_LANGUAGE)" \
		$(PROVIDER_CHECK_ARGS)

public-release-check:
	bash scripts/public_release_check.sh
