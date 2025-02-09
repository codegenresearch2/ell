import datetime\"nimport json\"nimport os\"nfrom typing import Any, Optional, Dict, List, Set, Union\"nfrom sqlmodel import Session, SQLModel, create_engine, select\"nimport ell.store\"nimport cattrs\"nimport numpy as np\"nfrom sqlalchemy.sql import text\"nfrom ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr\"nfrom ell.lstr import lstr\"nfrom sqlalchemy import or_, func, and_\"n\"nclass SQLStore(ell.store.Store):\"n    def __init__(self, db_uri: str):\"n        self.engine = create_engine(db_uri)\"n        SQLModel.metadata.create_all(self.engine)\"n        self.open_files: Dict[str, Dict[str, Any]] = {}\"n\"n    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str, \"n                  version_number: int,\"n                  uses: Dict[str, Any], \"n                  global_vars: Dict[str, Any],\"n                  free_vars: Dict[str, Any],\"n                  commit_message: Optional[str] = None,\"n                  created_at: Optional[float]=None) -> Optional[Any]:\"n        with Session(self.engine) as session:\"n            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()\"n            if lmp:\"n                return lmp\"n            else:\"n                lmp = SerializedLMP(\"n                    lmp_id=lmp_id,\"n                    name=name,\"n                    version_number=version_number,\"n                    source=source,\"n                    dependencies=dependencies,\"n                    initial_global_vars=global_vars,\"n                    initial_free_vars=free_vars,\"n                    created_at= created_at or datetime.datetime.utcnow(),\"n                    is_lm=is_lmp,\"n                    lm_kwargs=lm_kwargs,\"n                    commit_message=commit_message\"n                )\"n                session.add(lmp)\"n            for use_id in uses:\"n                used_lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == use_id).first()\"n                if used_lmp:\"n                    lmp.uses.append(used_lmp)\"n            session.commit()\"n        return None\"}n