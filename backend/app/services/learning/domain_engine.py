from typing import List, Dict

SUPPORTED_DOMAINS: Dict[str, List[str]] = {
    "dbms": [
        "Normalization",
        "Transactions",
        "Indexing",
        "Joins",
        "ACID Properties",
        "Deadlocks",
        "Database Architecture",
        "Concurrency Control"
    ],
    "sql": [
        "Write Joins",
        "Group By and Having Queries",
        "Subqueries",
        "Aggregations",
        "DDL vs DML",
        "Views and Indexes",
        "Window Functions",
        "Stored Procedures"
    ],
    "cn": [
        "OSI Model Layers",
        "TCP vs UDP",
        "IP Routing and Subnetting",
        "Congestion Control Algorithms",
        "DNS Protocol",
        "HTTP and HTTPS Protocols",
        "Socket Programming",
        "Flow Control (Sliding Window)"
    ],
    "os": [
        "Process Scheduling Algorithms",
        "Memory Management & Paging",
        "Deadlocks Detection and Prevention",
        "Virtual Memory & Page Replacement",
        "Threads and Concurrency",
        "System Calls",
        "Inter-Process Communication (IPC)",
        "Disk Scheduling"
    ],
    "oops": [
        "Classes and Objects",
        "Inheritance Types",
        "Polymorphism (Overloading & Overriding)",
        "Encapsulation",
        "Abstraction",
        "Interfaces vs Abstract Classes",
        "Constructors & Destructors",
        "Access Specifiers"
    ],
    "dsa": [
        "Arrays and Strings",
        "Hashmaps and Hash Sets",
        "Linked Lists",
        "Stacks and Queues",
        "Trees & Binary Search Trees",
        "Graphs & Graph Traversals",
        "Dynamic Programming",
        "Sorting & Searching Algorithms"
    ],
    "system_design": [
        "Load Balancers",
        "Caching Strategies",
        "Sharding & Replication",
        "Rate Limiters",
        "CAP Theorem",
        "CDN (Content Delivery Networks)",
        "Microservices Architecture",
        "Message Queues"
    ],
    "ml": [
        "Supervised Learning (Regression & Classification)",
        "Unsupervised Learning (Clustering & Dimensionality Reduction)",
        "Neural Networks & Deep Learning",
        "Feature Engineering & Selection",
        "Model Evaluation Metrics (Precision, Recall, ROC-AUC)",
        "Overfitting & Underfitting (Bias-Variance Tradeoff)",
        "Decision Trees & Random Forests",
        "Support Vector Machines"
    ]
}

def get_registered_domains() -> Dict[str, List[str]]:
    """Returns the dictionary of currently supported learning domains and standard topics."""
    return SUPPORTED_DOMAINS

def is_valid_domain(domain: str) -> bool:
    """Checks if a domain code is registered in the engine."""
    return domain.lower() in SUPPORTED_DOMAINS
