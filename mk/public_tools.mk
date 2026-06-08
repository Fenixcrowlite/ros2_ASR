PROVIDER_PRESET ?= light
PROVIDER_WAV ?= data/sample/vosk_test.wav
PROVIDER_LANGUAGE ?= en-US
PROVIDER_SETTINGS_JSON ?= {}
PROVIDER_CHECK_ARGS ?=

.PHONY: public-help init-provider-env provider-validate provider-test public-release-check prepare-ui-assets prepare-runtime-assets

prepare-ui-assets: setup-vosk

prepare-runtime-assets:
	@if [[ "$(PROVIDER_PROFILE)" == "providers/vosk_local" ]]; then \
		$(MAKE) setup-vosk; \
	else \
		printf '%s\n' 'No additional local runtime assets required for $(PROVIDER_PROFILE).'; \
	fi

up web-gui web-gui-lan: prepare-ui-assets
up-runtime: prepare-runtime-assets

public-help:
	@printf '%s\n' \
		'Public setup and provider commands:' \
		'  make up                                        Start the UI stack and prepare selectable local assets automatically' \
		'  make up-runtime PROVIDER_PROFILE=...            Start minimal runtime and prepare required local assets automatically' \
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
