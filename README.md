# Open Government Data

This project seeks to convert government data with the aim of providing a testbed for the implementation of the [linked data principles](http://www.w3.org/DesignIssues/LinkedData.html) advocated by [Tim Berners-Lee](https://en.wikipedia.org/wiki/Tim_Berners-Lee) and the [W3C](https://en.wikipedia.org/wiki/World_Wide_Web_Consortium).

## Rationale

The ecosystem of government data is essentially that of a decentralized knowledgebase. The W3C Semantic Web standards provide unique features in the context of decentralized data exchange:

* the use of [RDF](http://www.w3.org/RDF/) and [URLs](https://en.wikipedia.org/wiki/Uniform_resource_locator) provides a browsable, machine- and human-readable graph of government data using permalinks, enabling a web of data from previously disparate data islands;
* the [SPARQL](https://en.wikipedia.org/wiki/SPARQL) protocol provides a universal API via a graph database query service using HTTP and JSON;
* standardized vocabularies such as [GeoSPARQL](https://en.wikipedia.org/wiki/GeoSPARQL), the [Data Cube Vocabulary](http://www.w3.org/TR/vocab-data-cube/) and [Akoma Ntoso](http://www.akomantoso.org/) provide a common database schema for common datasets;
* [R2RML](http://www.w3.org/TR/r2rml/), [JSON-LD](https://en.wikipedia.org/wiki/JSON-LD) and the [Linked Data API](https://code.google.com/p/linked-data-api/wiki/Specification) provide the prospect of an incremental upgrade path for existing deployments.

