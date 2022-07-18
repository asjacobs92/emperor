nprintml \
  --concurrency 30 \
  --tcp \
  --ipv4 \
  --aggregator pcap \
  --count 5 \
  --nprint-filter "ipv4_src_[0-9]+|ipv4_dst_[0-9]+" \
  --compress \
  --label-file /data/temp/test/fixed-test-dataset/subset_labels \
  --save-nprint \
  --pcap-dir /data/temp/test/fixed-test-dataset/subset_pcaps \
  --output nprint_dataset/full_model_ucsb \
  --verbose \
  --quality 2 \
  --limit 30000