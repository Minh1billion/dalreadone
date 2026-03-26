import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useProjects,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
} from '../hooks/useProjects'
import { IconPlus, IconSearch } from '../components/ui/icons'
import ProjectCard from '../components/projects/ProjectCard'
import ProjectModal from '../components/projects/ProjectModal'
import DeleteConfirm from '../components/projects/DeleteConfirm'
import EmptyState from '../components/projects/EmptyState'
import type { Project } from '../api/project'

type Modal =
  | { type: 'create' }
  | { type: 'edit'; project: Project }
  | { type: 'delete'; project: Project }
  | null

export default function ProjectsPage() {
  const navigate = useNavigate()
  const [modal, setModal] = useState<Modal>(null)
  const [search, setSearch] = useState('')

  const { data: projects = [], isLoading, error } = useProjects()
  const createProject = useCreateProject()
  const updateProject = useUpdateProject()
  const deleteProject = useDeleteProject()

  const filtered = projects.filter((p: Project) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  )

  async function handleCreate(name: string) {
    await createProject.mutateAsync(name)
    setModal(null)
  }

  async function handleEdit(name: string) {
    if (modal?.type !== 'edit') return
    await updateProject.mutateAsync({ id: modal.project.id, name })
    setModal(null)
  }

  async function handleDelete() {
    if (modal?.type !== 'delete') return
    await deleteProject.mutateAsync(modal.project.id)
    setModal(null)
  }

  return (
    <>
      {modal?.type === 'create' && (
        <ProjectModal
          title="New project"
          loading={createProject.isPending}
          onConfirm={handleCreate}
          onClose={() => setModal(null)}
        />
      )}
      {modal?.type === 'edit' && (
        <ProjectModal
          title="Rename project"
          initialValue={modal.project.name}
          loading={updateProject.isPending}
          onConfirm={handleEdit}
          onClose={() => setModal(null)}
        />
      )}
      {modal?.type === 'delete' && (
        <DeleteConfirm
          projectName={modal.project.name}
          loading={deleteProject.isPending}
          onConfirm={handleDelete}
          onClose={() => setModal(null)}
        />
      )}

      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Projects</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {projects.length === 0
                ? 'No projects yet'
                : `${projects.length} project${projects.length !== 1 ? 's' : ''}`}
            </p>
          </div>
          <button
            onClick={() => setModal({ type: 'create' })}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-md transition-colors"
          >
            <IconPlus />
            New project
          </button>
        </div>

        {/* Search */}
        {projects.length > 0 && (
          <div className="relative mb-6">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              <IconSearch />
            </span>
            <input
              type="text"
              placeholder="Search projects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full max-w-xs pl-9 pr-3 py-2 border border-gray-200 rounded-md text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow"
            />
          </div>
        )}

        {/* Content */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-xl p-5 animate-pulse">
                <div className="w-10 h-10 bg-gray-100 rounded-lg mb-4" />
                <div className="h-3.5 bg-gray-100 rounded w-2/3 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-1/3" />
              </div>
            ))}
          </div>
        ) : error ? (
          <p className="text-sm text-red-500 py-8 text-center">
            Failed to load projects. Please try again.
          </p>
        ) : projects.length === 0 ? (
          <EmptyState onCreate={() => setModal({ type: 'create' })} />
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <p className="text-sm font-medium text-gray-900 mb-1">No results for "{search}"</p>
            <p className="text-sm text-gray-500">Try searching with a different name.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((project: Project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onOpen={() => navigate(`/projects/${project.id}`)}
                onEdit={() => setModal({ type: 'edit', project })}
                onDelete={() => setModal({ type: 'delete', project })}
              />
            ))}
          </div>
        )}
      </div>
    </>
  )
}