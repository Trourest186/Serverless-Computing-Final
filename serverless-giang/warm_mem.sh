data={'"'data'"':{'"'concurrencyStateEndpoint'"':'"'http://
address=$1
end=:9696'"'}}

json=$data$address$end
#echo $json
kubectl patch configmap/config-deployment -n knative-serving --type merge -p $json