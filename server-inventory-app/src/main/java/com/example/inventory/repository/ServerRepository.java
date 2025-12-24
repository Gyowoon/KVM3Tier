package com.example.inventory.repository;

import com.example.inventory.entity.ServerInfo;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.transaction.Transactional;
import java.util.List;
import java.util.Optional;

@ApplicationScoped
public class ServerRepository {

    @PersistenceContext(unitName = "InventoryPU")
    private EntityManager em;

    public List<ServerInfo> findAll() {
        return em.createNamedQuery("ServerInfo.findAll", ServerInfo.class).getResultList();
    }

    public Optional<ServerInfo> findById(Long id) {
        return Optional.ofNullable(em.find(ServerInfo.class, id));
    }

    @Transactional
    public ServerInfo save(ServerInfo server) {
        if (server.getId() == null) {
            em.persist(server);
            return server;
        } else {
            return em.merge(server);
        }
    }

    @Transactional
    public void delete(Long id) {
        findById(id).ifPresent(em::remove);
    }
}
