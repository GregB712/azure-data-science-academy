import Layout from './components/Layout'
import { useRoute } from './lib/router'
import Architecture from './pages/Architecture'
import Catalog from './pages/Catalog'
import DocPage from './pages/DocPage'
import FileView from './pages/FileView'
import Glossary from './pages/Glossary'
import Home from './pages/Home'
import Labs from './pages/Labs'
import NotFound from './pages/NotFound'
import ProgressPage from './pages/ProgressPage'
import SearchPage from './pages/SearchPage'
import Services from './pages/Services'

export default function App() {
  const route = useRoute()
  let page
  switch (route.page) {
    case '':
      page = <Home />
      break
    case 'doc':
      page = <DocPage route={route.rest} section={route.params.get('s')} />
      break
    case 'catalog':
      page = <Catalog params={route.params} />
      break
    case 'labs':
      page = <Labs />
      break
    case 'architecture':
      page = <Architecture selected={route.params.get('v')} />
      break
    case 'services':
      page = <Services focus={route.params.get('s')} />
      break
    case 'glossary':
      page = <Glossary focus={route.params.get('t')} />
      break
    case 'search':
      page = <SearchPage query={route.params.get('q') ?? ''} />
      break
    case 'file':
      page = <FileView path={route.rest} />
      break
    case 'progress':
      page = <ProgressPage />
      break
    default:
      page = <NotFound what={route.params.get('p') ?? route.page} />
  }
  return <Layout>{page}</Layout>
}
