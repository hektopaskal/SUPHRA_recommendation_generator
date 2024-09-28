# work in progress

'''
Get papers suggested by Semantic Scholar Recommendation API
'''
papers = ["f712fab0d58ae6492e3cdfc1933dae103ec12d5d",
          "649def34f8be52c8b66281af98ae884c09aef38b"]
paper_id: str
paper_ids = []

recommendation = {
    paper_id: [{
        "tip": str,
        "information": str,
        "category": str,
        "goal": str,
        "focus": str,
        "activity_type": str,
        "daytime": str,
        "weekday": str,
        "source": str,
        "author's": str,
        "publication_title": str,
        "year": int,
        "citation_count": int, # + influentialCitationCount ??
        "authors_total_citation_count": int, # if paper has been released recently authors_total_citation_count could be more informative than citation_count
        "source_retracted": bool,
        "journal": str,
        # journal quality data from paperQA2
    }]
}

for paperid in paper_ids:
