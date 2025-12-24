package com.example.inventory.resource;

import com.example.inventory.entity.ServerInfo;
import com.example.inventory.repository.ServerRepository;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.List;

@Path("/servers")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class ServerResource {

    @Inject
    private ServerRepository repository;

    @GET
    public List<ServerInfo> getAll() {
        return repository.findAll();
    }

    @GET
    @Path("/{id}")
    public Response getById(@PathParam("id") Long id) {
        return repository.findById(id)
                .map(server -> Response.ok(server).build())
                .orElse(Response.status(Response.Status.NOT_FOUND).build());
    }

    @POST
    public Response create(ServerInfo server) {
        ServerInfo saved = repository.save(server);
        return Response.status(Response.Status.CREATED).entity(saved).build();
    }

    @PUT
    @Path("/{id}")
    public Response update(@PathParam("id") Long id, ServerInfo server) {
        return repository.findById(id)
                .map(existing -> {
                    server.setId(id);
                    return Response.ok(repository.save(server)).build();
                })
                .orElse(Response.status(Response.Status.NOT_FOUND).build());
    }

    @DELETE
    @Path("/{id}")
    public Response delete(@PathParam("id") Long id) {
        return repository.findById(id)
                .map(server -> {
                    repository.delete(id);
                    return Response.noContent().build();
                })
                .orElse(Response.status(Response.Status.NOT_FOUND).build());
    }

    @GET
    @Path("/health")
    public Response health() {
        return Response.ok("{\"status\":\"UP\"}").build();
    }
}
