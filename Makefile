DEMO_DIR ?= data/demo

.PHONY: demo-alarms demo-alarms-data demo-alarms-encode

demo: demo-profiles demo-events demo-tags demo-viewer
	@echo "✅ Demo completa in $(DEMO_DIR)"

demo-alarms: demo-alarms-encode
	@echo "✅ Demo allarmi completata (alarms_intensity.lsg2 incluso nei profili)"

demo-alarms-data:
	python tools/generate_fake_alarms.py $(DEMO_DIR)/alarms.csv
	python tools/prep_alarms.py \
		$(DEMO_DIR)/alarms.csv \
		$(DEMO_DIR)/alarms_intensity.csv \
		--dt 60

demo-alarms-encode: demo-alarms-data
	lasagna2 encode \
		--dt 60 \
		--t0 2025-01-01T00:00:30 \
		--unit s \
		$(DEMO_DIR)/alarms_intensity.csv \
		$(DEMO_DIR)/alarms_intensity.lsg2

demo-data:
	python tools/generate_demo_data.py

demo-encode: demo-data
	lasagna2 encode --dt 1 --t0 0 --unit step \
		$(DEMO_DIR)/trend.csv \
		$(DEMO_DIR)/trend.lsg2
	lasagna2 encode --dt 1 --t0 0 --unit step \
		$(DEMO_DIR)/sine_noise.csv \
		$(DEMO_DIR)/sine_noise.lsg2
	lasagna2 encode --dt 1 --t0 0 --unit step \
		$(DEMO_DIR)/flat_spike.csv \
		$(DEMO_DIR)/flat_spike.lsg2
	lasagna2 encode --dt 1 --t0 0 --unit step \
		$(DEMO_DIR)/ramp_then_burst.csv \
		$(DEMO_DIR)/ramp_then_burst.lsg2
	lasagna2 encode --dt 1 --t0 0 --unit step \
		$(DEMO_DIR)/multi_bump.csv \
		$(DEMO_DIR)/multi_bump.lsg2

demo-profiles: demo-encode demo-alarms-encode
	python tools/batch_profile.py $(DEMO_DIR) -o $(DEMO_DIR)/profiles.csv

demo-events: demo-profiles
	python tools/semantic_events.py $(DEMO_DIR)/profiles.csv $(DEMO_DIR)/events.csv
	python tools/cluster_profiles.py $(DEMO_DIR)/profiles.csv $(DEMO_DIR)/clusters.csv

demo-tags: demo-encode
	lasagna2 export-tags $(DEMO_DIR)/trend.lsg2      $(DEMO_DIR)/trend_tags.csv
	lasagna2 export-tags $(DEMO_DIR)/sine_noise.lsg2 $(DEMO_DIR)/sine_noise_tags.csv
	lasagna2 export-tags $(DEMO_DIR)/flat_spike.lsg2 $(DEMO_DIR)/flat_spike_tags.csv

demo-viewer: demo-tags
	python tools/lasagna_viewer.py $(DEMO_DIR)/flat_spike_tags.csv
	python tools/alarms_intensity_viewer.py $(DEMO_DIR)/alarms_intensity.csv
